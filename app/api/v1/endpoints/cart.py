"""
CorePath Impact Shopping Cart Endpoints
API endpoints for shopping cart management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.core.database import get_db
from app.models.user import User
from app.services.cart_service import CartService
from app.schemas.order import (
    CartItemAdd, CartItemUpdate, CartResponse, CartItemResponse,
    CheckoutSummary, ShippingCalculation, ShippingRate
)
from app.schemas.auth import MessageResponse
from app.api.deps import get_current_user

router = APIRouter()


def get_cart_service(db: Session = Depends(get_db)) -> CartService:
    """Get cart service instance"""
    return CartService(db)


@router.get("/", response_model=CartResponse)
async def get_cart(
    current_user: User = Depends(get_current_user),
    cart_service: CartService = Depends(get_cart_service)
):
    """
    Get current user's shopping cart
    
    Returns cart with all items and calculated totals
    """
    try:
        cart = cart_service.get_cart_with_items(current_user.id)
        
        # Convert to response format
        cart_items = []
        for item in cart.items:
            product = item.product
            variant = item.variant
            
            cart_item_data = {
                "id": item.id,
                "product_id": product.id,
                "product_name": product.name,
                "product_slug": product.slug,
                "product_image": product.primary_image,
                "variant_id": variant.id if variant else None,
                "variant_name": variant.name if variant else None,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "total_price": item.total_price,
                "is_available": item.is_available,
                "created_at": item.created_at
            }
            cart_items.append(CartItemResponse(**cart_item_data))
        
        return CartResponse(
            id=cart.id,
            user_id=cart.user_id,
            items=cart_items,
            subtotal=cart.subtotal,
            item_count=cart.item_count,
            updated_at=cart.updated_at
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve cart"
        )


@router.post("/add", response_model=CartItemResponse)
async def add_to_cart(
    item_data: CartItemAdd,
    current_user: User = Depends(get_current_user),
    cart_service: CartService = Depends(get_cart_service)
):
    """
    Add item to shopping cart
    
    - **product_id**: Product ID to add
    - **variant_id**: Optional product variant ID
    - **quantity**: Quantity to add (1-100)
    
    If item already exists in cart, quantities will be combined
    """
    try:
        cart_item = cart_service.add_item(current_user.id, item_data)
        
        # Convert to response format
        product = cart_item.product
        variant = cart_item.variant
        
        return CartItemResponse(
            id=cart_item.id,
            product_id=product.id,
            product_name=product.name,
            product_slug=product.slug,
            product_image=product.primary_image,
            variant_id=variant.id if variant else None,
            variant_name=variant.name if variant else None,
            quantity=cart_item.quantity,
            unit_price=cart_item.unit_price,
            total_price=cart_item.total_price,
            is_available=cart_item.is_available,
            created_at=cart_item.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add item to cart"
        )


@router.put("/items/{item_id}", response_model=CartItemResponse)
async def update_cart_item(
    item_id: int,
    item_data: CartItemUpdate,
    current_user: User = Depends(get_current_user),
    cart_service: CartService = Depends(get_cart_service)
):
    """
    Update cart item quantity
    
    - **quantity**: New quantity (0 to remove item)
    
    Set quantity to 0 to remove item from cart
    """
    try:
        cart_item = cart_service.update_item(current_user.id, item_id, item_data)
        
        if not cart_item:
            return MessageResponse(
                message="Item removed from cart",
                success=True
            )
        
        # Convert to response format
        product = cart_item.product
        variant = cart_item.variant
        
        return CartItemResponse(
            id=cart_item.id,
            product_id=product.id,
            product_name=product.name,
            product_slug=product.slug,
            product_image=product.primary_image,
            variant_id=variant.id if variant else None,
            variant_name=variant.name if variant else None,
            quantity=cart_item.quantity,
            unit_price=cart_item.unit_price,
            total_price=cart_item.total_price,
            is_available=cart_item.is_available,
            created_at=cart_item.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update cart item"
        )


@router.delete("/items/{item_id}", response_model=MessageResponse)
async def remove_from_cart(
    item_id: int,
    current_user: User = Depends(get_current_user),
    cart_service: CartService = Depends(get_cart_service)
):
    """Remove item from shopping cart"""
    try:
        success = cart_service.remove_item(current_user.id, item_id)
        return MessageResponse(
            message="Item removed from cart successfully",
            success=success
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove item from cart"
        )


@router.delete("/clear", response_model=MessageResponse)
async def clear_cart(
    current_user: User = Depends(get_current_user),
    cart_service: CartService = Depends(get_cart_service)
):
    """Clear all items from shopping cart"""
    try:
        success = cart_service.clear_cart(current_user.id)
        return MessageResponse(
            message="Cart cleared successfully",
            success=success
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear cart"
        )


@router.get("/summary", response_model=CheckoutSummary)
async def get_cart_summary(
    current_user: User = Depends(get_current_user),
    cart_service: CartService = Depends(get_cart_service)
):
    """
    Get cart summary with calculated totals
    
    Returns detailed cart summary including:
    - All cart items
    - Calculated totals (subtotal, shipping, tax, total)
    - Available shipping methods
    - User's available points
    """
    try:
        cart_summary = cart_service.get_cart_summary(current_user.id)
        cart = cart_summary["cart"]
        
        # Convert cart items to response format
        cart_items = []
        for item in cart.items:
            if not item.is_available:
                continue
                
            product = item.product
            variant = item.variant
            
            cart_item_data = {
                "id": item.id,
                "product_id": product.id,
                "product_name": product.name,
                "product_slug": product.slug,
                "product_image": product.primary_image,
                "variant_id": variant.id if variant else None,
                "variant_name": variant.name if variant else None,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "total_price": item.total_price,
                "is_available": item.is_available,
                "created_at": item.created_at
            }
            cart_items.append(CartItemResponse(**cart_item_data))
        
        # Get available shipping methods (basic implementation)
        shipping_methods = [
            ShippingRate(
                method="standard",
                name="Standard Shipping",
                description="5-7 business days",
                cost=cart_summary["shipping_cost"],
                estimated_days=7
            )
        ]
        
        # Get user's available points
        user_profile = current_user.profile
        available_points = user_profile.current_points_balance if user_profile else 0
        points_value = available_points * 0.01  # 1 point = 0.01 KES
        
        return CheckoutSummary(
            items=cart_items,
            subtotal=cart_summary["subtotal"],
            tax_amount=cart_summary["tax_amount"],
            shipping_amount=cart_summary["shipping_cost"],
            discount_amount=0.0,
            points_discount=0.0,
            total_amount=cart_summary["total"],
            available_shipping_methods=shipping_methods,
            points_available=available_points,
            points_value=points_value
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get cart summary"
        )


@router.post("/shipping-rates", response_model=List[ShippingRate])
async def get_shipping_rates(
    shipping_calculation: ShippingCalculation,
    current_user: User = Depends(get_current_user),
    cart_service: CartService = Depends(get_cart_service)
):
    """
    Calculate shipping rates for cart items and address
    
    - **items**: List of items to ship
    - **shipping_address**: Destination address
    
    Returns available shipping methods with costs
    """
    try:
        # For now, return the shipping rates from cart service
        # In a real implementation, this would integrate with shipping carriers
        rates_data = cart_service.get_shipping_rates(
            current_user.id,
            shipping_calculation.shipping_address.dict()
        )
        
        shipping_rates = []
        for rate_data in rates_data:
            shipping_rates.append(ShippingRate(**rate_data))
        
        return shipping_rates
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate shipping rates"
        )


@router.post("/validate", response_model=Dict[str, Any])
async def validate_cart_for_checkout(
    current_user: User = Depends(get_current_user),
    cart_service: CartService = Depends(get_cart_service)
):
    """
    Validate cart is ready for checkout
    
    Checks:
    - Cart is not empty
    - All items are available
    - Sufficient inventory for all items
    - Returns any errors or warnings
    """
    try:
        validation_result = cart_service.validate_cart_for_checkout(current_user.id)
        return validation_result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate cart"
        )


@router.get("/count")
async def get_cart_count(
    current_user: User = Depends(get_current_user),
    cart_service: CartService = Depends(get_cart_service)
):
    """
    Get cart item count
    
    Returns just the number of items in cart for header display
    """
    try:
        cart = cart_service.get_cart_with_items(current_user.id)
        return {
            "item_count": cart.item_count,
            "total_items": sum(item.quantity for item in cart.items if item.is_available)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get cart count"
        )


@router.post("/sync-prices")
async def sync_cart_prices(
    current_user: User = Depends(get_current_user),
    cart_service: CartService = Depends(get_cart_service)
):
    """
    Sync cart item prices with current product prices
    
    Updates cart item prices to match current product/variant prices
    Useful when prices change after items are added to cart
    """
    try:
        cart = cart_service.get_cart_with_items(current_user.id)
        
        updated_count = 0
        for item in cart.items:
            old_price = item.unit_price
            item.calculate_total()  # This updates price based on current product price
            
            if item.unit_price != old_price:
                updated_count += 1
        
        # Update cart totals
        cart.calculate_totals()
        cart_service.db.commit()
        
        return {
            "message": f"Cart prices synchronized. {updated_count} items updated.",
            "updated_items": updated_count,
            "success": True
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to sync cart prices"
        )