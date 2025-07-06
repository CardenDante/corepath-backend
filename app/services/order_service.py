# app/services/order_service.py - Created by setup script
"""
CorePath Impact Order Service
Business logic for order management and processing
"""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc, asc
from fastapi import HTTPException, status
from datetime import datetime, timedelta
import uuid

from app.models.order import Order, OrderItem, Payment, Coupon, CouponUsage, OrderStatus, PaymentStatus
from app.models.product import Product, ProductVariant
from app.models.user import User, UserProfile
from app.schemas.order import OrderCreate, OrderUpdate, PaymentCreate, OrderFilters
from app.utils.helpers import generate_order_number, paginate_query
from app.core.config import settings


class OrderService:
    """Service for order management operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_order(self, user_id: int, order_data: OrderCreate) -> Order:
        """Create a new order from order data"""
        # Get user information
        user = self.db.query(User).options(joinedload(User.profile)).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Validate and calculate order items
        order_items = []
        subtotal = 0.0
        
        for item_data in order_data.items:
            # Validate product
            product = self.db.query(Product).filter(Product.id == item_data.product_id).first()
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Product with ID {item_data.product_id} not found"
                )
            
            if not product.is_in_stock:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Product '{product.name}' is out of stock"
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
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Product variant with ID {item_data.variant_id} not found"
                    )
                
                if not variant.is_in_stock or not variant.is_active:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Product variant '{variant.name}' is not available"
                    )
            
            # Check inventory
            available_quantity = variant.inventory_count if variant else product.inventory_count
            if product.track_inventory and available_quantity < item_data.quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Only {available_quantity} units of '{product.name}' available"
                )
            
            # Calculate pricing
            unit_price = variant.final_price if variant else product.price
            total_price = unit_price * item_data.quantity
            
            # Create order item
            order_item = {
                "product_id": product.id,
                "variant_id": variant.id if variant else None,
                "product_name": product.name,
                "product_sku": product.sku,
                "variant_name": variant.name if variant else None,
                "quantity": item_data.quantity,
                "unit_price": unit_price,
                "total_price": total_price,
                "product_snapshot": {
                    "id": product.id,
                    "name": product.name,
                    "description": product.short_description,
                    "price": product.price,
                    "image_url": product.primary_image
                }
            }
            
            order_items.append(order_item)
            subtotal += total_price
        
        # Calculate shipping
        shipping_amount = self._calculate_shipping_cost(order_data.shipping_method, order_items, order_data.shipping_address)
        
        # Apply coupon discount if provided
        discount_amount = 0.0
        coupon = None
        if order_data.coupon_code:
            coupon, discount_amount = self._apply_coupon(order_data.coupon_code, subtotal, user_id)
        
        # Apply points discount if requested
        points_discount = 0.0
        points_used = 0
        if order_data.use_points and user.profile:
            points_discount, points_used = self._apply_points_discount(
                order_data.use_points, subtotal, user.profile.current_points_balance
            )
        
        # Calculate tax (if applicable)
        tax_amount = 0.0  # No tax for now
        
        # Calculate total
        total_amount = subtotal + shipping_amount + tax_amount - discount_amount - points_discount
        total_amount = max(0, total_amount)  # Ensure total is not negative
        
        # Generate order number
        order_number = generate_order_number()
        
        # Create order
        order = Order(
            order_number=order_number,
            user_id=user_id,
            customer_email=user.email,
            customer_name=user.full_name,
            customer_phone=user.phone,
            subtotal=subtotal,
            tax_amount=tax_amount,
            shipping_amount=shipping_amount,
            discount_amount=discount_amount,
            points_discount=points_discount,
            total_amount=total_amount,
            shipping_method=order_data.shipping_method,
            shipping_address=order_data.shipping_address.dict(),
            billing_address=order_data.billing_address.dict() if order_data.billing_address else order_data.shipping_address.dict(),
            notes=order_data.notes,
            is_gift=order_data.is_gift,
            gift_message=order_data.gift_message,
            points_used=points_used
        )
        
        # Calculate points earned
        order.calculate_points_earned(settings.ORDER_POINTS_RATE)
        
        self.db.add(order)
        self.db.flush()  # Get order ID
        
        # Add order items
        for item_data in order_items:
            order_item = OrderItem(
                order_id=order.id,
                **item_data
            )
            self.db.add(order_item)
        
        # Update inventory
        for item_data in order_data.items:
            product = self.db.query(Product).filter(Product.id == item_data.product_id).first()
            if product.track_inventory:
                if item_data.variant_id:
                    variant = self.db.query(ProductVariant).filter(ProductVariant.id == item_data.variant_id).first()
                    variant.inventory_count = max(0, variant.inventory_count - item_data.quantity)
                else:
                    product.decrease_inventory(item_data.quantity)
                
                # Increment purchase count
                product.increment_purchase_count(item_data.quantity)
        
        # Update user points
        if points_used > 0 and user.profile:
            user.profile.spend_points(points_used)
        
        # Record coupon usage
        if coupon:
            coupon_usage = CouponUsage(
                coupon_id=coupon.id,
                user_id=user_id,
                order_id=order.id,
                discount_amount=discount_amount
            )
            self.db.add(coupon_usage)
            coupon.usage_count += 1
        
        self.db.commit()
        self.db.refresh(order)
        
        return order
    
    def get_order_by_id(self, order_id: int, user_id: Optional[int] = None) -> Optional[Order]:
        """Get order by ID with optional user filter"""
        query = self.db.query(Order).options(
            joinedload(Order.items).joinedload(OrderItem.product),
            joinedload(Order.items).joinedload(OrderItem.variant),
            joinedload(Order.payments)
        )
        
        if user_id:
            query = query.filter(Order.user_id == user_id)
        
        return query.filter(Order.id == order_id).first()
    
    def get_order_by_number(self, order_number: str, user_id: Optional[int] = None) -> Optional[Order]:
        """Get order by order number with optional user filter"""
        query = self.db.query(Order).options(
            joinedload(Order.items),
            joinedload(Order.payments)
        )
        
        if user_id:
            query = query.filter(Order.user_id == user_id)
        
        return query.filter(Order.order_number == order_number).first()
    
    def get_user_orders(
        self,
        user_id: int,
        page: int = 1,
        per_page: int = 20,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get user's orders with pagination"""
        query = self.db.query(Order).filter(Order.user_id == user_id)
        
        if status:
            query = query.filter(Order.status == status)
        
        query = query.order_by(desc(Order.created_at))
        
        return paginate_query(query, page, per_page)
    
    def search_orders(
        self,
        filters: OrderFilters,
        page: int = 1,
        per_page: int = 20
    ) -> Dict[str, Any]:
        """Search orders with filters and pagination"""
        query = self.db.query(Order)
        
        # Apply filters
        if filters.status:
            query = query.filter(Order.status == filters.status)
        
        if filters.payment_status:
            # This requires a more complex query to check payment status
            if filters.payment_status == "completed":
                query = query.join(Payment).filter(Payment.status == PaymentStatus.COMPLETED.value)
            elif filters.payment_status == "pending":
                query = query.filter(~Order.payments.any(Payment.status == PaymentStatus.COMPLETED.value))
        
        if filters.customer_email:
            query = query.filter(Order.customer_email.ilike(f"%{filters.customer_email}%"))
        
        if filters.date_from:
            query = query.filter(Order.created_at >= filters.date_from)
        
        if filters.date_to:
            query = query.filter(Order.created_at <= filters.date_to)
        
        if filters.min_amount is not None:
            query = query.filter(Order.total_amount >= filters.min_amount)
        
        if filters.max_amount is not None:
            query = query.filter(Order.total_amount <= filters.max_amount)
        
        # Apply sorting
        sort_field = getattr(Order, filters.sort_by, Order.created_at)
        if filters.sort_order == "asc":
            query = query.order_by(asc(sort_field))
        else:
            query = query.order_by(desc(sort_field))
        
        return paginate_query(query, page, per_page)
    
    def update_order(self, order_id: int, order_data: OrderUpdate) -> Order:
        """Update order (admin only)"""
        order = self.db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        update_data = order_data.dict(exclude_unset=True)
        
        # Handle status changes
        if 'status' in update_data and update_data['status'] != order.status:
            old_status = order.status
            new_status = update_data['status']
            
            # Validate status transition
            if not self._is_valid_status_transition(old_status, new_status):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot change order status from '{old_status}' to '{new_status}'"
                )
            
            # Handle special status changes
            if new_status == OrderStatus.SHIPPED.value:
                order.shipped_at = datetime.utcnow()
            elif new_status == OrderStatus.DELIVERED.value:
                order.delivered_at = datetime.utcnow()
                # Award points to user when order is delivered
                self._award_order_points(order)
        
        # Apply updates
        for field, value in update_data.items():
            setattr(order, field, value)
        
        self.db.commit()
        self.db.refresh(order)
        
        return order
    
    def cancel_order(self, order_id: int, user_id: Optional[int] = None, reason: str = None) -> Order:
        """Cancel an order"""
        query = self.db.query(Order).filter(Order.id == order_id)
        
        if user_id:
            query = query.filter(Order.user_id == user_id)
        
        order = query.first()
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        if not order.can_cancel:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order cannot be cancelled in its current status"
            )
        
        # Cancel order
        order.status = OrderStatus.CANCELLED.value
        if reason:
            order.admin_notes = f"Cancelled: {reason}"
        
        # Restore inventory
        for item in order.items:
            product = item.product
            if product.track_inventory:
                if item.variant_id:
                    variant = item.variant
                    variant.inventory_count += item.quantity
                else:
                    product.increase_inventory(item.quantity)
        
        # Refund points if used
        if order.points_used > 0:
            user = order.user
            if user.profile:
                user.profile.add_points(order.points_used, "Order cancellation refund")
        
        self.db.commit()
        self.db.refresh(order)
        
        return order
    
    def create_payment(self, payment_data: PaymentCreate) -> Payment:
        """Create a payment record for an order"""
        order = self.db.query(Order).filter(Order.id == payment_data.order_id).first()
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        # Determine payment amount
        amount = payment_data.amount if payment_data.amount else order.total_amount
        
        # Check if order is already fully paid
        if order.is_paid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order is already fully paid"
            )
        
        payment = Payment(
            order_id=order.id,
            amount=amount,
            currency=order.currency,
            payment_method=payment_data.payment_method,
            status=PaymentStatus.PENDING.value
        )
        
        self.db.add(payment)
        self.db.commit()
        self.db.refresh(payment)
        
        return payment
    
    def process_payment(self, payment_id: int, external_payment_id: str, status: str, details: Dict[str, Any] = None) -> Payment:
        """Process payment status update from payment provider"""
        payment = self.db.query(Payment).filter(Payment.id == payment_id).first()
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )
        
        payment.external_payment_id = external_payment_id
        payment.payment_details = details
        
        if status == PaymentStatus.COMPLETED.value:
            payment.mark_completed()
            
            # Update order status if fully paid
            order = payment.order
            if order.is_paid and order.status == OrderStatus.PENDING.value:
                order.status = OrderStatus.PROCESSING.value
        
        elif status == PaymentStatus.FAILED.value:
            failure_reason = details.get('failure_reason') if details else None
            payment.mark_failed(failure_reason)
        
        else:
            payment.status = status
        
        self.db.commit()
        self.db.refresh(payment)
        
        return payment
    
    def _calculate_shipping_cost(self, method: str, items: List[Dict], address: Dict) -> float:
        """Calculate shipping cost based on method and items"""
        # Check if all items are digital
        all_digital = all(item.get('product_snapshot', {}).get('is_digital', False) for item in items)
        if all_digital:
            return 0.0
        
        # Basic shipping calculation
        country = address.get('country', '').lower()
        
        if method == "standard":
            return 10.0 if country == "kenya" else 25.0
        elif method == "express":
            return 25.0 if country == "kenya" else 50.0
        elif method == "overnight":
            return 50.0 if country == "kenya" else 100.0
        else:
            return 10.0
    
    def _apply_coupon(self, coupon_code: str, order_amount: float, user_id: int) -> Tuple[Optional[Coupon], float]:
        """Apply coupon discount to order"""
        coupon = self.db.query(Coupon).filter(Coupon.code == coupon_code.upper()).first()
        
        if not coupon:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid coupon code"
            )
        
        if not coupon.is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Coupon is not valid or has expired"
            )
        
        # Check user usage limit
        if coupon.usage_limit_per_user:
            user_usage_count = self.db.query(CouponUsage).filter(
                CouponUsage.coupon_id == coupon.id,
                CouponUsage.user_id == user_id
            ).count()
            
            if user_usage_count >= coupon.usage_limit_per_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Coupon usage limit exceeded"
                )
        
        discount_amount = coupon.calculate_discount(order_amount)
        
        if discount_amount == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Order does not meet minimum amount requirement of {coupon.minimum_order_amount}"
            )
        
        return coupon, discount_amount
    
    def _apply_points_discount(self, points_requested: int, order_amount: float, available_points: int) -> Tuple[float, int]:
        """Apply points discount to order"""
        if points_requested > available_points:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient points. You have {available_points} points available"
            )
        
        # Points value (configurable)
        points_value = 0.01  # 1 point = 0.01 KES
        
        # Calculate maximum discount (cannot exceed order amount)
        max_discount = order_amount
        requested_discount = points_requested * points_value
        
        actual_discount = min(requested_discount, max_discount)
        actual_points_used = int(actual_discount / points_value)
        
        return actual_discount, actual_points_used
    
    def _is_valid_status_transition(self, from_status: str, to_status: str) -> bool:
        """Check if status transition is valid"""
        valid_transitions = {
            OrderStatus.PENDING.value: [OrderStatus.PROCESSING.value, OrderStatus.CANCELLED.value],
            OrderStatus.PROCESSING.value: [OrderStatus.SHIPPED.value, OrderStatus.CANCELLED.value],
            OrderStatus.SHIPPED.value: [OrderStatus.DELIVERED.value],
            OrderStatus.DELIVERED.value: [OrderStatus.REFUNDED.value],
            OrderStatus.CANCELLED.value: [],
            OrderStatus.REFUNDED.value: []
        }
        
        return to_status in valid_transitions.get(from_status, [])
    
    def _award_order_points(self, order: Order):
        """Award points to user when order is delivered"""
        if order.points_earned > 0:
            user = order.user
            if user.profile:
                user.profile.add_points(
                    order.points_earned,
                    f"Points earned from order {order.order_number}"
                )
    
    def get_order_statistics(self) -> Dict[str, Any]:
        """Get order statistics for admin dashboard"""
        total_orders = self.db.query(Order).count()
        
        # Orders by status
        status_counts = {}
        for status in OrderStatus:
            count = self.db.query(Order).filter(Order.status == status.value).count()
            status_counts[status.value] = count
        
        # Revenue statistics
        total_revenue = self.db.query(func.sum(Order.total_amount)).filter(
            Order.status.in_([OrderStatus.DELIVERED.value, OrderStatus.SHIPPED.value])
        ).scalar() or 0
        
        # Average order value
        avg_order_value = self.db.query(func.avg(Order.total_amount)).scalar() or 0
        
        # Recent orders (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_orders = self.db.query(Order).filter(Order.created_at >= thirty_days_ago).count()
        
        return {
            "total_orders": total_orders,
            "status_counts": status_counts,
            "total_revenue": float(total_revenue),
            "average_order_value": float(avg_order_value),
            "recent_orders": recent_orders,
            "pending_orders": status_counts.get(OrderStatus.PENDING.value, 0),
            "processing_orders": status_counts.get(OrderStatus.PROCESSING.value, 0)
        }
    
    def get_revenue_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get revenue analytics for specified period"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Daily revenue
        daily_revenue = self.db.query(
            func.date(Order.created_at).label('date'),
            func.sum(Order.total_amount).label('revenue'),
            func.count(Order.id).label('orders')
        ).filter(
            Order.created_at >= start_date,
            Order.status.in_([OrderStatus.DELIVERED.value, OrderStatus.SHIPPED.value, OrderStatus.PROCESSING.value])
        ).group_by(func.date(Order.created_at)).order_by(func.date(Order.created_at)).all()
        
        # Top products by revenue
        top_products = self.db.query(
            OrderItem.product_name,
            func.sum(OrderItem.total_price).label('revenue'),
            func.sum(OrderItem.quantity).label('quantity')
        ).join(Order).filter(
            Order.created_at >= start_date,
            Order.status.in_([OrderStatus.DELIVERED.value, OrderStatus.SHIPPED.value, OrderStatus.PROCESSING.value])
        ).group_by(OrderItem.product_name).order_by(desc('revenue')).limit(10).all()
        
        return {
            "period_days": days,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "daily_revenue": [
                {
                    "date": str(row.date),
                    "revenue": float(row.revenue),
                    "orders": row.orders
                }
                for row in daily_revenue
            ],
            "top_products": [
                {
                    "product_name": row.product_name,
                    "revenue": float(row.revenue),
                    "quantity": row.quantity
                }
                for row in top_products
            ]
        }
