"""
CorePath Impact Cart Service
Business logic for shopping cart management
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status

from app.models.order import ShoppingCart, CartItem
from app.models.product import Product, ProductVariant
from app.models.user import User
from app.schemas.order import CartItemAdd, CartItemUpdate


class CartService:
    """Service for shopping cart operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_or_create_cart(self, user_id: int) -> ShoppingCart:
        """Get existing cart or create new one for user"""
        cart = self.db.query(ShoppingCart).filter(ShoppingCart.user_id == user_id).first()
        
        if not cart:
            cart = ShoppingCart(user_id=user_id)
            self.db.add(cart)
            self.db.commit()
            self.db.refresh(cart)
        
        return cart
    
    def get_cart_with_items(self, user_id: int) -> ShoppingCart:
        """Get cart with all items and related product data"""
        cart = self.db.query(ShoppingCart).options(
            joinedload(ShoppingCart.items).joinedload(CartItem.product),
            joinedload(ShoppingCart.items).joinedload(CartItem.variant)
        ).filter(ShoppingCart.user_id == user_id).first()
        
        if not cart:
            cart = self.get_or_create_cart(user_id)
        
        return cart
    
    def add_item(self, user_id: int, item_data: CartItemAdd) -> CartItem:
        """Add item to cart or update quantity if exists"""
        # Validate product exists and is available
        product = self.db.query(Product).filter(Product.id == item_data.product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        if not product.is_in_stock:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Product is out of stock"
            )
        
        # Validate variant if specified
        variant = None
        if item_data.variant_id:
            variant = self.db.query(ProductVariant).filter(
                ProductVariant.id == item_data.variant_id,
                ProductVariant.product_id == item_data.product_id
            ).first()
            
            if not variant:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Product variant not found"
                )
            
            if not variant.is_in_stock or not variant.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Product variant is not available"
                )
        
        # Check inventory availability
        available_quantity = variant.inventory_count if variant else product.inventory_count
        if product.track_inventory and available_quantity < item_data.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Only {available_quantity} items available in stock"
            )
        
        # Get or create cart
        cart = self.get_or_create_cart(user_id)
        
        # Check if item already exists in cart
        existing_item = self.db.query(CartItem).filter(
            CartItem.cart_id == cart.id,
            CartItem.product_id == item_data.product_id,
            CartItem.variant_id == item_data.variant_id
        ).first()
        
        if existing_item:
            # Update quantity
            new_quantity = existing_item.quantity + item_data.quantity
            
            # Check total quantity against inventory
            if product.track_inventory and available_quantity < new_quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot add {item_data.quantity} more items. Only {available_quantity - existing_item.quantity} additional items available"
                )
            
            existing_item.quantity = new_quantity
            existing_item.calculate_total()
            cart_item = existing_item
        else:
            # Create new cart item
            cart_item = CartItem(
                cart_id=cart.id,
                product_id=item_data.product_id,
                variant_id=item_data.variant_id,
                quantity=item_data.quantity
            )
            cart_item.calculate_total()
            self.db.add(cart_item)
        
        # Update cart totals
        cart.calculate_totals()
        
        self.db.commit()
        self.db.refresh(cart_item)
        
        return cart_item
    
    def update_item(self, user_id: int, item_id: int, item_data: CartItemUpdate) -> Optional[CartItem]:
        """Update cart item quantity"""
        # Get cart item
        cart_item = self.db.query(CartItem).join(ShoppingCart).filter(
            CartItem.id == item_id,
            ShoppingCart.user_id == user_id
        ).first()
        
        if not cart_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cart item not found"
            )
        
        # If quantity is 0, remove item
        if item_data.quantity == 0:
            return self.remove_item(user_id, item_id)
        
        # Validate inventory availability
        product = cart_item.product
        variant = cart_item.variant
        
        available_quantity = variant.inventory_count if variant else product.inventory_count
        if product.track_inventory and available_quantity < item_data.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Only {available_quantity} items available in stock"
            )
        
        # Update quantity
        cart_item.quantity = item_data.quantity
        cart_item.calculate_total()
        
        # Update cart totals
        cart = cart_item.cart
        cart.calculate_totals()
        
        self.db.commit()
        self.db.refresh(cart_item)
        
        return cart_item
    
    def remove_item(self, user_id: int, item_id: int) -> bool:
        """Remove item from cart"""
        cart_item = self.db.query(CartItem).join(ShoppingCart).filter(
            CartItem.id == item_id,
            ShoppingCart.user_id == user_id
        ).first()
        
        if not cart_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cart item not found"
            )
        
        cart = cart_item.cart
        self.db.delete(cart_item)
        
        # Update cart totals
        cart.calculate_totals()
        
        self.db.commit()
        
        return True
    
    def clear_cart(self, user_id: int) -> bool:
        """Clear all items from cart"""
        cart = self.db.query(ShoppingCart).filter(ShoppingCart.user_id == user_id).first()
        
        if not cart:
            return True
        
        # Delete all cart items
        self.db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
        
        # Update cart totals
        cart.calculate_totals()
        
        self.db.commit()
        
        return True
    
    def get_cart_summary(self, user_id: int) -> Dict[str, Any]:
        """Get cart summary with calculated totals"""
        cart = self.get_cart_with_items(user_id)
        
        # Calculate totals
        subtotal = sum(item.total_price for item in cart.items if item.is_available)
        item_count = sum(item.quantity for item in cart.items if item.is_available)
        unavailable_items = [item for item in cart.items if not item.is_available]
        
        # Calculate shipping (basic logic - can be enhanced)
        shipping_cost = self._calculate_shipping(cart.items)
        
        # Calculate tax (if applicable)
        tax_rate = 0.0  # No tax for now
        tax_amount = subtotal * tax_rate
        
        total = subtotal + shipping_cost + tax_amount
        
        return {
            "cart": cart,
            "subtotal": subtotal,
            "item_count": item_count,
            "shipping_cost": shipping_cost,
            "tax_amount": tax_amount,
            "total": total,
            "unavailable_items": unavailable_items,
            "has_unavailable_items": len(unavailable_items) > 0
        }
    
    def _calculate_shipping(self, items: List[CartItem]) -> float:
        """Calculate shipping cost for cart items"""
        if not items:
            return 0.0
        
        # Check if all items are digital
        all_digital = all(item.product.is_digital for item in items if item.is_available)
        if all_digital:
            return 0.0
        
        # Basic shipping calculation
        # In a real implementation, this would consider:
        # - Shipping address
        # - Item weight/dimensions
        # - Shipping method
        # - Carrier rates
        
        total_weight = sum(
            (item.product.weight or 0) * item.quantity 
            for item in items 
            if item.is_available and not item.product.is_digital
        )
        
        if total_weight == 0:
            return 10.0  # Base shipping rate
        elif total_weight <= 1000:  # 1kg
            return 10.0
        elif total_weight <= 5000:  # 5kg
            return 15.0
        else:
            return 20.0
    
    def validate_cart_for_checkout(self, user_id: int) -> Dict[str, Any]:
        """Validate cart is ready for checkout"""
        cart_summary = self.get_cart_summary(user_id)
        
        errors = []
        warnings = []
        
        # Check if cart is empty
        if cart_summary["item_count"] == 0:
            errors.append("Cart is empty")
        
        # Check for unavailable items
        if cart_summary["has_unavailable_items"]:
            warnings.append("Some items in your cart are no longer available")
        
        # Validate inventory for each item
        for item in cart_summary["cart"].items:
            if not item.is_available:
                continue
            
            product = item.product
            variant = item.variant
            
            if product.track_inventory:
                available = variant.inventory_count if variant else product.inventory_count
                if available < item.quantity:
                    errors.append(
                        f"Only {available} units of '{product.name}' are available, "
                        f"but {item.quantity} are in your cart"
                    )
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "cart_summary": cart_summary
        }
    
    def get_shipping_rates(self, user_id: int, shipping_address: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get available shipping rates for cart"""
        cart = self.get_cart_with_items(user_id)
        
        if not cart.items:
            return []
        
        # Check if all items are digital
        all_digital = all(item.product.is_digital for item in cart.items if item.is_available)
        if all_digital:
            return [{
                "method": "digital",
                "name": "Digital Delivery",
                "description": "Instant download",
                "cost": 0.0,
                "estimated_days": 0
            }]
        
        # Basic shipping rates based on location
        # In a real implementation, this would integrate with shipping carriers
        country = shipping_address.get("country", "").lower()
        
        rates = []
        
        if country == "kenya":
            rates = [
                {
                    "method": "standard",
                    "name": "Standard Shipping",
                    "description": "5-7 business days",
                    "cost": 10.0,
                    "estimated_days": 7
                },
                {
                    "method": "express",
                    "name": "Express Shipping",
                    "description": "2-3 business days",
                    "cost": 25.0,
                    "estimated_days": 3
                }
            ]
        else:
            rates = [
                {
                    "method": "international",
                    "name": "International Shipping",
                    "description": "10-14 business days",
                    "cost": 50.0,
                    "estimated_days": 14
                }
            ]
        
        return rates
    
    def cleanup_expired_carts(self, days_old: int = 30) -> int:
        """Clean up old abandoned carts"""
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        # Find old carts
        old_carts = self.db.query(ShoppingCart).filter(
            ShoppingCart.updated_at < cutoff_date
        ).all()
        
        deleted_count = 0
        for cart in old_carts:
            # Delete cart items first (due to foreign key constraints)
            self.db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
            self.db.delete(cart)
            deleted_count += 1
        
        self.db.commit()
        
        return deleted_count
    
    def migrate_guest_cart(self, session_id: str, user_id: int) -> bool:
        """Migrate guest cart to user cart (for future implementation)"""
        # This would be used when implementing guest checkout
        # For now, just return True as we only support authenticated users
        return True