# app/services/product_service.py - Created by setup script
"""
CorePath Impact Product Service
Business logic for product and category management
"""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc, asc
from fastapi import HTTPException, status
import re

from app.models.product import Product, Category, ProductImage, ProductVariant, ProductStatus
from app.schemas.product import (
    ProductCreate, ProductUpdate, CategoryCreate, CategoryUpdate,
    ProductSearchFilters, ProductImageCreate, ProductVariantCreate
)
from app.utils.helpers import slugify, paginate_query


class ProductService:
    """Service for product management operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # Category Management
    def create_category(self, category_data: CategoryCreate) -> Category:
        """Create a new product category"""
        # Generate slug from name
        slug = slugify(category_data.name)
        
        # Check if slug already exists
        existing = self.db.query(Category).filter(Category.slug == slug).first()
        if existing:
            # Add number suffix if slug exists
            counter = 1
            while existing:
                new_slug = f"{slug}-{counter}"
                existing = self.db.query(Category).filter(Category.slug == new_slug).first()
                counter += 1
            slug = new_slug
        
        # Validate parent category if specified
        if category_data.parent_id:
            parent = self.db.query(Category).filter(Category.id == category_data.parent_id).first()
            if not parent:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Parent category not found"
                )
        
        category = Category(
            name=category_data.name,
            slug=slug,
            description=category_data.description,
            parent_id=category_data.parent_id,
            icon=category_data.icon,
            sort_order=category_data.sort_order,
            is_active=category_data.is_active,
            meta_title=category_data.meta_title,
            meta_description=category_data.meta_description
        )
        
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        
        return category
    
    def get_category_by_id(self, category_id: int) -> Optional[Category]:
        """Get category by ID"""
        return self.db.query(Category).filter(Category.id == category_id).first()
    
    def get_category_by_slug(self, slug: str) -> Optional[Category]:
        """Get category by slug"""
        return self.db.query(Category).filter(Category.slug == slug).first()
    
    def get_categories(
        self, 
        parent_id: Optional[int] = None,
        is_active: Optional[bool] = True,
        include_children: bool = False
    ) -> List[Category]:
        """Get categories with optional filtering"""
        query = self.db.query(Category)
        
        if parent_id is not None:
            query = query.filter(Category.parent_id == parent_id)
        
        if is_active is not None:
            query = query.filter(Category.is_active == is_active)
        
        if include_children:
            query = query.options(joinedload(Category.children))
        
        return query.order_by(Category.sort_order, Category.name).all()
    
    def update_category(self, category_id: int, category_data: CategoryUpdate) -> Category:
        """Update a category"""
        category = self.get_category_by_id(category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
        
        # Update fields
        update_data = category_data.dict(exclude_unset=True)
        
        # Handle name change (regenerate slug)
        if 'name' in update_data and update_data['name'] != category.name:
            new_slug = slugify(update_data['name'])
            # Check for slug conflicts
            existing = self.db.query(Category).filter(
                Category.slug == new_slug,
                Category.id != category_id
            ).first()
            
            if existing:
                counter = 1
                while existing:
                    test_slug = f"{new_slug}-{counter}"
                    existing = self.db.query(Category).filter(
                        Category.slug == test_slug,
                        Category.id != category_id
                    ).first()
                    counter += 1
                new_slug = test_slug
            
            update_data['slug'] = new_slug
        
        # Validate parent category
        if 'parent_id' in update_data and update_data['parent_id']:
            if update_data['parent_id'] == category_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Category cannot be its own parent"
                )
            
            parent = self.db.query(Category).filter(Category.id == update_data['parent_id']).first()
            if not parent:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Parent category not found"
                )
        
        # Apply updates
        for field, value in update_data.items():
            setattr(category, field, value)
        
        self.db.commit()
        self.db.refresh(category)
        
        return category
    
    def delete_category(self, category_id: int) -> bool:
        """Delete a category (only if no products)"""
        category = self.get_category_by_id(category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
        
        # Check if category has products
        product_count = self.db.query(Product).filter(Product.category_id == category_id).count()
        if product_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete category with {product_count} products"
            )
        
        # Check if category has children
        children_count = self.db.query(Category).filter(Category.parent_id == category_id).count()
        if children_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete category with {children_count} subcategories"
            )
        
        self.db.delete(category)
        self.db.commit()
        
        return True
    
    # Product Management
    def create_product(self, product_data: ProductCreate) -> Product:
        """Create a new product"""
        # Validate category exists
        category = self.get_category_by_id(product_data.category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category not found"
            )
        
        # Generate slug from name
        slug = slugify(product_data.name)
        
        # Check if slug already exists
        existing = self.db.query(Product).filter(Product.slug == slug).first()
        if existing:
            counter = 1
            while existing:
                new_slug = f"{slug}-{counter}"
                existing = self.db.query(Product).filter(Product.slug == new_slug).first()
                counter += 1
            slug = new_slug
        
        # Check SKU uniqueness if provided
        if product_data.sku:
            existing_sku = self.db.query(Product).filter(Product.sku == product_data.sku).first()
            if existing_sku:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="SKU already exists"
                )
        
        product = Product(
            name=product_data.name,
            slug=slug,
            sku=product_data.sku,
            short_description=product_data.short_description,
            description=product_data.description,
            price=product_data.price,
            compare_at_price=product_data.compare_at_price,
            category_id=product_data.category_id,
            inventory_count=product_data.inventory_count,
            track_inventory=product_data.track_inventory,
            allow_backorder=product_data.allow_backorder,
            status=ProductStatus.ACTIVE.value,
            is_featured=product_data.is_featured,
            is_digital=product_data.is_digital,
            weight=product_data.weight,
            dimensions=product_data.dimensions,
            tags=product_data.tags,
            meta_title=product_data.meta_title,
            meta_description=product_data.meta_description
        )
        
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        
        return product
    
    def get_product_by_id(self, product_id: int, include_relations: bool = True) -> Optional[Product]:
        """Get product by ID with optional relations"""
        query = self.db.query(Product)
        
        if include_relations:
            query = query.options(
                joinedload(Product.category),
                joinedload(Product.images),
                joinedload(Product.variants)
            )
        
        return query.filter(Product.id == product_id).first()
    
    def get_product_by_slug(self, slug: str, include_relations: bool = True) -> Optional[Product]:
        """Get product by slug with optional relations"""
        query = self.db.query(Product)
        
        if include_relations:
            query = query.options(
                joinedload(Product.category),
                joinedload(Product.images),
                joinedload(Product.variants)
            )
        
        product = query.filter(Product.slug == slug).first()
        
        # Increment view count
        if product:
            product.increment_view_count()
            self.db.commit()
        
        return product
    
    def search_products(
        self,
        filters: ProductSearchFilters,
        page: int = 1,
        per_page: int = 20
    ) -> Dict[str, Any]:
        """Search products with filters and pagination"""
        query = self.db.query(Product).options(joinedload(Product.category))
        
        # Apply filters
        if filters.q:
            search_term = f"%{filters.q}%"
            query = query.filter(
                or_(
                    Product.name.ilike(search_term),
                    Product.short_description.ilike(search_term),
                    Product.description.ilike(search_term)
                )
            )
        
        if filters.category_id:
            query = query.filter(Product.category_id == filters.category_id)
        
        if filters.min_price is not None:
            query = query.filter(Product.price >= filters.min_price)
        
        if filters.max_price is not None:
            query = query.filter(Product.price <= filters.max_price)
        
        if filters.is_featured is not None:
            query = query.filter(Product.is_featured == filters.is_featured)
        
        if filters.is_digital is not None:
            query = query.filter(Product.is_digital == filters.is_digital)
        
        if filters.in_stock:
            query = query.filter(
                or_(
                    Product.track_inventory == False,
                    and_(
                        Product.track_inventory == True,
                        or_(
                            Product.inventory_count > 0,
                            Product.allow_backorder == True
                        )
                    )
                )
            )
        
        if filters.tags:
            # Filter by tags (assuming tags are stored as JSON array)
            for tag in filters.tags:
                query = query.filter(func.json_extract(Product.tags, '$').like(f'%{tag}%'))
        
        # Apply sorting
        sort_field = getattr(Product, filters.sort_by, Product.created_at)
        if filters.sort_order == "asc":
            query = query.order_by(asc(sort_field))
        else:
            query = query.order_by(desc(sort_field))
        
        # Apply pagination
        return paginate_query(query, page, per_page)
    
    def get_featured_products(self, limit: int = 10) -> List[Product]:
        """Get featured products"""
        return self.db.query(Product).options(joinedload(Product.category)).filter(
            Product.is_featured == True,
            Product.status == ProductStatus.ACTIVE.value
        ).order_by(desc(Product.created_at)).limit(limit).all()
    
    def get_products_by_category(
        self,
        category_id: int,
        page: int = 1,
        per_page: int = 20,
        include_subcategories: bool = False
    ) -> Dict[str, Any]:
        """Get products by category with pagination"""
        query = self.db.query(Product).options(joinedload(Product.category))
        
        if include_subcategories:
            # Get all subcategory IDs
            subcategories = self.db.query(Category.id).filter(Category.parent_id == category_id).all()
            subcategory_ids = [sub[0] for sub in subcategories]
            subcategory_ids.append(category_id)
            
            query = query.filter(Product.category_id.in_(subcategory_ids))
        else:
            query = query.filter(Product.category_id == category_id)
        
        query = query.filter(Product.status == ProductStatus.ACTIVE.value)
        query = query.order_by(desc(Product.is_featured), desc(Product.created_at))
        
        return paginate_query(query, page, per_page)
    
    def update_product(self, product_id: int, product_data: ProductUpdate) -> Product:
        """Update a product"""
        product = self.get_product_by_id(product_id, include_relations=False)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        update_data = product_data.dict(exclude_unset=True)
        
        # Handle name change (regenerate slug)
        if 'name' in update_data and update_data['name'] != product.name:
            new_slug = slugify(update_data['name'])
            existing = self.db.query(Product).filter(
                Product.slug == new_slug,
                Product.id != product_id
            ).first()
            
            if existing:
                counter = 1
                while existing:
                    test_slug = f"{new_slug}-{counter}"
                    existing = self.db.query(Product).filter(
                        Product.slug == test_slug,
                        Product.id != product_id
                    ).first()
                    counter += 1
                new_slug = test_slug
            
            update_data['slug'] = new_slug
        
        # Validate category if changed
        if 'category_id' in update_data:
            category = self.get_category_by_id(update_data['category_id'])
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Category not found"
                )
        
        # Check SKU uniqueness if changed
        if 'sku' in update_data and update_data['sku'] != product.sku:
            existing_sku = self.db.query(Product).filter(
                Product.sku == update_data['sku'],
                Product.id != product_id
            ).first()
            if existing_sku:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="SKU already exists"
                )
        
        # Apply updates
        for field, value in update_data.items():
            setattr(product, field, value)
        
        self.db.commit()
        self.db.refresh(product)
        
        return product
    
    def delete_product(self, product_id: int) -> bool:
        """Delete a product"""
        product = self.get_product_by_id(product_id, include_relations=False)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        # TODO: Check if product has orders before deletion
        # For now, just mark as inactive
        product.status = ProductStatus.INACTIVE.value
        self.db.commit()
        
        return True
    
    # Product Images
    def add_product_image(
        self,
        product_id: int,
        image_data: ProductImageCreate,
        image_url: str
    ) -> ProductImage:
        """Add an image to a product"""
        product = self.get_product_by_id(product_id, include_relations=False)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        # If this is set as primary, unset other primary images
        if image_data.is_primary:
            self.db.query(ProductImage).filter(
                ProductImage.product_id == product_id,
                ProductImage.is_primary == True
            ).update({"is_primary": False})
        
        product_image = ProductImage(
            product_id=product_id,
            image_url=image_url,
            alt_text=image_data.alt_text,
            caption=image_data.caption,
            is_primary=image_data.is_primary,
            sort_order=image_data.sort_order
        )
        
        self.db.add(product_image)
        self.db.commit()
        self.db.refresh(product_image)
        
        return