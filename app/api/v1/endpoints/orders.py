# app/api/v1/endpoints/orders.py - Created by setup script
"""
CorePath Impact Order Management Endpoints
API endpoints for order processing and management
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from app.core.database import get_db
from app.models.user import User
from app.services.order_service import OrderService
from app.services.cart_service import CartService
from app.schemas.order import (
    OrderCreate, OrderUpdate, OrderResponse, OrderListResponse,
    PaymentCreate, PaymentResponse, PaymentIntent,
    OrderFilters, PaginatedOrderResponse, OrderStats, RevenueStats
)
from app.schemas.auth import MessageResponse
from app.api.deps import get_current_user, get_current_admin_user, pagination_params

router = APIRouter()


def get_order_service(db: Session = Depends(get_db)) -> OrderService:
    """Get order service instance"""
    return OrderService(db)


def get_cart_service(db: Session = Depends(get_db)) -> CartService:
    """Get cart service instance"""
    return CartService(db)


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    current_user: User = Depends(get_current_user),
    order_service: OrderService = Depends(get_order_service),
    cart_service: CartService = Depends(get_cart_service)
):
    """
    Create a new order
    
    - **items**: List of products and quantities to order
    - **shipping_address**: Delivery address
    - **billing_address**: Billing address (optional, defaults to shipping)
    - **shipping_method**: Shipping method (standard, express, etc.)
    - **payment_method**: Payment method (card, mobile_money, etc.)
    - **use_points**: Number of points to use for discount
    - **coupon_code**: Coupon code for discount
    - **notes**: Order notes
    - **is_gift**: Mark as gift order
    - **gift_message**: Gift message
    
    Creates order and clears user's cart
    """
    try:
        # Create the order
        order = order_service.create_order(current_user.id, order_data)
        
        # Clear user's cart after successful order creation
        cart_service.clear_cart(current_user.id)
        
        return OrderResponse.from_orm(order)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create order"
        )


@router.get("/", response_model=PaginatedOrderResponse)
async def list_user_orders(
    status_filter: Optional[str] = Query(None, alias="status"),
    pagination: dict = Depends(pagination_params),
    current_user: User = Depends(get_current_user),
    order_service: OrderService = Depends(get_order_service)
):
    """
    List current user's orders
    
    - **status**: Filter by order status (optional)
    - **page**: Page number
    - **limit**: Items per page
    
    Returns paginated list of user's orders
    """
    try:
        result = order_service.get_user_orders(
            current_user.id,
            pagination["page"],
            pagination["limit"],
            status_filter
        )
        
        # Convert to list response format
        orders = []
        for order in result["items"]:
            order_data = {
                "id": order.id,
                "order_number": order.order_number,
                "status": order.status,
                "customer_name": order.customer_name,
                "customer_email": order.customer_email,
                "item_count": order.item_count,
                "total_amount": order.total_amount,
                "currency": order.currency,
                "is_paid": order.is_paid,
                "payment_status": order.payment_status,
                "created_at": order.created_at
            }
            orders.append(OrderListResponse(**order_data))
        
        return PaginatedOrderResponse(
            items=orders,
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
            detail="Failed to retrieve orders"
        )


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    order_service: OrderService = Depends(get_order_service)
):
    """Get order details by ID (user can only access their own orders)"""
    order = order_service.get_order_by_id(order_id, current_user.id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    return OrderResponse.from_orm(order)


@router.get("/number/{order_number}", response_model=OrderResponse)
async def get_order_by_number(
    order_number: str,
    current_user: User = Depends(get_current_user),
    order_service: OrderService = Depends(get_order_service)
):
    """Get order details by order number (user can only access their own orders)"""
    order = order_service.get_order_by_number(order_number, current_user.id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    return OrderResponse.from_orm(order)


@router.put("/{order_id}/cancel", response_model=OrderResponse)
async def cancel_order(
    order_id: int,
    reason: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    order_service: OrderService = Depends(get_order_service)
):
    """
    Cancel an order
    
    - **reason**: Optional cancellation reason
    
    User can only cancel their own orders and only if in cancellable status
    """
    try:
        order = order_service.cancel_order(order_id, current_user.id, reason)
        return OrderResponse.from_orm(order)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel order"
        )


# Payment Endpoints
@router.post("/{order_id}/payments", response_model=PaymentResponse)
async def create_payment(
    order_id: int,
    payment_data: PaymentCreate,
    current_user: User = Depends(get_current_user),
    order_service: OrderService = Depends(get_order_service)
):
    """
    Create a payment for an order
    
    - **payment_method**: Payment method (card, mobile_money, etc.)
    - **amount**: Payment amount (optional, defaults to order total)
    
    Creates payment record and returns payment details for processing
    """
    try:
        # Verify user owns the order
        order = order_service.get_order_by_id(order_id, current_user.id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        # Create payment
        payment_data.order_id = order_id
        payment = order_service.create_payment(payment_data)
        
        return PaymentResponse.from_orm(payment)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create payment"
        )


@router.post("/{order_id}/payment-intent", response_model=PaymentIntent)
async def create_payment_intent(
    order_id: int,
    payment_method: str = "card",
    current_user: User = Depends(get_current_user),
    order_service: OrderService = Depends(get_order_service)
):
    """
    Create payment intent for Stripe or other payment processors
    
    - **payment_method**: Payment method type
    
    Returns client secret for frontend payment processing
    """
    try:
        # Verify user owns the order
        order = order_service.get_order_by_id(order_id, current_user.id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        if order.is_paid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order is already paid"
            )
        
        # Create payment intent
        # In a real implementation, this would integrate with Stripe
        payment_intent = {
            "client_secret": f"pi_{order.id}_{current_user.id}_secret_mock",
            "amount": order.total_amount,
            "currency": order.currency.lower(),
            "payment_method_types": ["card"] if payment_method == "card" else [payment_method]
        }
        
        return PaymentIntent(**payment_intent)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create payment intent"
        )


# Admin Endpoints
@router.get("/admin/orders", response_model=PaginatedOrderResponse)
async def list_all_orders(
    status_filter: Optional[str] = Query(None, alias="status"),
    payment_status: Optional[str] = Query(None),
    customer_email: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    min_amount: Optional[float] = Query(None),
    max_amount: Optional[float] = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    pagination: dict = Depends(pagination_params),
    admin_user: User = Depends(get_current_admin_user),
    order_service: OrderService = Depends(get_order_service)
):
    """
    List all orders with filtering (Admin only)
    
    - **status**: Filter by order status
    - **payment_status**: Filter by payment status
    - **customer_email**: Filter by customer email
    - **date_from / date_to**: Date range filter
    - **min_amount / max_amount**: Amount range filter
    - **sort_by**: Sort field
    - **sort_order**: Sort order (asc/desc)
    """
    try:
        from datetime import datetime
        
        # Convert date strings to datetime objects
        date_from_dt = None
        date_to_dt = None
        
        if date_from:
            date_from_dt = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
        if date_to:
            date_to_dt = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
        
        filters = OrderFilters(
            status=status_filter,
            payment_status=payment_status,
            customer_email=customer_email,
            date_from=date_from_dt,
            date_to=date_to_dt,
            min_amount=min_amount,
            max_amount=max_amount,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        result = order_service.search_orders(
            filters,
            pagination["page"],
            pagination["limit"]
        )
        
        # Convert to list response format
        orders = []
        for order in result["items"]:
            order_data = {
                "id": order.id,
                "order_number": order.order_number,
                "status": order.status,
                "customer_name": order.customer_name,
                "customer_email": order.customer_email,
                "item_count": order.item_count,
                "total_amount": order.total_amount,
                "currency": order.currency,
                "is_paid": order.is_paid,
                "payment_status": order.payment_status,
                "created_at": order.created_at
            }
            orders.append(OrderListResponse(**order_data))
        
        return PaginatedOrderResponse(
            items=orders,
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
            detail="Failed to retrieve orders"
        )


@router.get("/admin/orders/{order_id}", response_model=OrderResponse)
async def get_order_admin(
    order_id: int,
    admin_user: User = Depends(get_current_admin_user),
    order_service: OrderService = Depends(get_order_service)
):
    """Get order details by ID (Admin only)"""
    order = order_service.get_order_by_id(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    return OrderResponse.from_orm(order)


@router.put("/admin/orders/{order_id}", response_model=OrderResponse)
async def update_order_admin(
    order_id: int,
    order_data: OrderUpdate,
    admin_user: User = Depends(get_current_admin_user),
    order_service: OrderService = Depends(get_order_service)
):
    """
    Update order (Admin only)
    
    - **status**: Update order status
    - **tracking_number**: Add tracking number
    - **admin_notes**: Add admin notes
    - **shipping_method**: Update shipping method
    """
    try:
        order = order_service.update_order(order_id, order_data)
        return OrderResponse.from_orm(order)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update order"
        )


@router.put("/admin/orders/{order_id}/cancel", response_model=OrderResponse)
async def cancel_order_admin(
    order_id: int,
    reason: Optional[str] = None,
    admin_user: User = Depends(get_current_admin_user),
    order_service: OrderService = Depends(get_order_service)
):
    """Cancel an order (Admin only)"""
    try:
        order = order_service.cancel_order(order_id, None, reason)
        return OrderResponse.from_orm(order)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel order"
        )


# Analytics Endpoints
@router.get("/admin/analytics/stats", response_model=OrderStats)
async def get_order_statistics(
    admin_user: User = Depends(get_current_admin_user),
    order_service: OrderService = Depends(get_order_service)
):
    """Get order statistics (Admin only)"""
    try:
        stats = order_service.get_order_statistics()
        
        return OrderStats(
            total_orders=stats["total_orders"],
            pending_orders=stats["pending_orders"],
            processing_orders=stats["processing_orders"],
            shipped_orders=stats["status_counts"].get("shipped", 0),
            delivered_orders=stats["status_counts"].get("delivered", 0),
            cancelled_orders=stats["status_counts"].get("cancelled", 0),
            total_revenue=stats["total_revenue"],
            average_order_value=stats["average_order_value"]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve order statistics"
        )


@router.get("/admin/analytics/revenue", response_model=RevenueStats)
async def get_revenue_analytics(
    days: int = Query(30, ge=1, le=365),
    admin_user: User = Depends(get_current_admin_user),
    order_service: OrderService = Depends(get_order_service)
):
    """
    Get revenue analytics (Admin only)
    
    - **days**: Number of days to analyze (1-365)
    
    Returns daily revenue, weekly revenue, monthly revenue, and top products
    """
    try:
        analytics = order_service.get_revenue_analytics(days)
        
        return RevenueStats(
            daily_revenue=analytics["daily_revenue"],
            weekly_revenue=[],  # Can be implemented if needed
            monthly_revenue=[],  # Can be implemented if needed
            top_products=analytics["top_products"]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve revenue analytics"
        )


# Webhook Endpoints (for payment providers)
@router.post("/webhooks/payment-status")
async def payment_webhook(
    payment_data: Dict[str, Any],
    order_service: OrderService = Depends(get_order_service)
):
    """
    Webhook endpoint for payment status updates
    
    Used by payment providers (Stripe, M-Pesa, etc.) to notify payment status changes
    """
    try:
        # Extract payment information from webhook data
        # This would be customized based on the payment provider's webhook format
        
        payment_id = payment_data.get("payment_id")
        external_payment_id = payment_data.get("external_payment_id")
        status = payment_data.get("status")
        details = payment_data.get("details", {})
        
        if not all([payment_id, external_payment_id, status]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required payment data"
            )
        
        # Process payment status update
        payment = order_service.process_payment(payment_id, external_payment_id, status, details)
        
        return {
            "message": "Payment status updated successfully",
            "payment_id": payment.id,
            "status": payment.status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process payment webhook"
        )