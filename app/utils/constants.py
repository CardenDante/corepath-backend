# app/utils/constants.py - Created by setup script
"""
CorePath Impact Application Constants
Centralized constants used throughout the application
"""

from enum import Enum


# User Roles
class UserRole(Enum):
    CUSTOMER = "customer"
    MERCHANT = "merchant"
    ADMIN = "admin"


# Order Status
class OrderStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


# Payment Status
class PaymentStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


# Merchant Status
class MerchantStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUSPENDED = "suspended"


# Point Transaction Types
class PointTransactionType(Enum):
    EARNED_SIGNUP = "earned_signup"
    EARNED_PURCHASE = "earned_purchase"
    EARNED_REFERRAL = "earned_referral"
    EARNED_BONUS = "earned_bonus"
    SPENT_DISCOUNT = "spent_discount"
    SPENT_REWARD = "spent_reward"
    EXPIRED = "expired"
    ADJUSTED = "adjusted"


# Course Status
class CourseStatus(Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


# Enrollment Status
class EnrollmentStatus(Enum):
    ENROLLED = "enrolled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DROPPED = "dropped"


# File Upload Constants
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif', 'webp']
ALLOWED_DOCUMENT_EXTENSIONS = ['pdf', 'doc', 'docx', 'txt']

# Upload Directories
UPLOAD_DIRS = {
    'products': 'uploads/products',
    'users': 'uploads/users',
    'courses': 'uploads/courses',
    'documents': 'uploads/documents'
}

# Pagination Defaults
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# Points System
POINTS_CONFIG = {
    'signup_bonus': 100,
    'referral_reward': 500,
    'purchase_rate': 0.01,  # 1% of purchase amount
    'min_redemption': 100,
    'expiry_days': 365
}

# Email Templates
EMAIL_TEMPLATES = {
    'welcome': 'welcome_email.html',
    'verification': 'email_verification.html',
    'password_reset': 'password_reset.html',
    'order_confirmation': 'order_confirmation.html',
    'merchant_approval': 'merchant_approval.html'
}

# Notification Types
class NotificationType(Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"


# Product Categories (Initial set)
PRODUCT_CATEGORIES = {
    'toolkits': 'VDC Toolkits',
    'books': 'Books & Guides',
    'cards': 'Training Cards',
    'courses': 'Online Courses',
    'accessories': 'Accessories',
    'digital': 'Digital Downloads'
}

# Course Age Groups
COURSE_AGE_GROUPS = {
    'early': '4-9 years',
    'middle': '10-14 years',
    'teen': '15-18 years',
    'all': 'All ages'
}

# API Rate Limits
RATE_LIMITS = {
    'auth': '5/minute',
    'general': '100/minute',
    'upload': '10/minute',
    'admin': '200/minute'
}

# Countries (Common ones for the platform)
COUNTRIES = [
    'Kenya',
    'Uganda',
    'Tanzania',
    'Rwanda',
    'Nigeria',
    'Ghana',
    'South Africa',
    'United States',
    'United Kingdom',
    'Canada',
    'Australia'
]

# Currencies
CURRENCIES = [
    'KES',  # Kenyan Shilling
    'USD',  # US Dollar
    'EUR',  # Euro
    'GBP'   # British Pound
]

# Time Zones
TIMEZONES = [
    'Africa/Nairobi',
    'UTC',
    'America/New_York',
    'Europe/London'
]

# Error Messages
ERROR_MESSAGES = {
    'INVALID_CREDENTIALS': 'Invalid email or password',
    'EMAIL_EXISTS': 'Email already registered',
    'USER_NOT_FOUND': 'User not found',
    'ACCOUNT_DISABLED': 'Account is disabled',
    'EMAIL_NOT_VERIFIED': 'Email not verified',
    'INVALID_TOKEN': 'Invalid or expired token',
    'INSUFFICIENT_PERMISSIONS': 'Insufficient permissions',
    'INSUFFICIENT_POINTS': 'Insufficient points balance',
    'FILE_TOO_LARGE': 'File size exceeds maximum limit',
    'INVALID_FILE_TYPE': 'Invalid file type',
    'PRODUCT_NOT_FOUND': 'Product not found',
    'ORDER_NOT_FOUND': 'Order not found',
    'PAYMENT_FAILED': 'Payment processing failed',
    'MERCHANT_NOT_APPROVED': 'Merchant account not approved'
}

# Success Messages
SUCCESS_MESSAGES = {
    'USER_REGISTERED': 'User registered successfully',
    'LOGIN_SUCCESS': 'Login successful',
    'LOGOUT_SUCCESS': 'Logout successful',
    'EMAIL_VERIFIED': 'Email verified successfully',
    'PASSWORD_CHANGED': 'Password changed successfully',
    'PROFILE_UPDATED': 'Profile updated successfully',
    'ORDER_CREATED': 'Order created successfully',
    'PAYMENT_SUCCESS': 'Payment processed successfully',
    'MERCHANT_APPLIED': 'Merchant application submitted',
    'POINTS_REDEEMED': 'Points redeemed successfully'
}

# Regex Patterns
REGEX_PATTERNS = {
    'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
    'phone_kenya': r'^(\+254|0)[71][0-9]{8}$',
    'password': r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d@$!%*?&]{8,}$',
    'slug': r'^[a-z0-9-]+$'
}

# VDC Values (Core values for the platform)
VDC_VALUES = [
    'Respect',
    'Honesty',
    'Responsibility',
    'Kindness',
    'Patience',
    'Gratitude',
    'Diligence',
    'Integrity',
    'Empathy',
    'Self-Control',
    'Perseverance',
    'Generosity',
    'Humility',
    'Courage',
    'Compassion',
    'Forgiveness',
    'Loyalty',
    'Justice',
    'Wisdom',
    'Faith',
    'Hope',
    'Love',
    'Service',
    'Excellence'
]

# Default Settings
DEFAULT_SETTINGS = {
    'currency': 'KES',
    'timezone': 'Africa/Nairobi',
    'language': 'en',
    'email_notifications': True,
    'sms_notifications': False,
    'newsletter_subscribed': True
}

# API Response Codes
API_RESPONSE_CODES = {
    'SUCCESS': 200,
    'CREATED': 201,
    'NO_CONTENT': 204,
    'BAD_REQUEST': 400,
    'UNAUTHORIZED': 401,
    'FORBIDDEN': 403,
    'NOT_FOUND': 404,
    'CONFLICT': 409,
    'VALIDATION_ERROR': 422,
    'SERVER_ERROR': 500
}

# Cache Keys
CACHE_KEYS = {
    'user_profile': 'user_profile_{user_id}',
    'product_list': 'product_list_{page}_{category}',
    'course_list': 'course_list_{page}',
    'merchant_stats': 'merchant_stats_{merchant_id}'
}

# Task Queue Names
TASK_QUEUES = {
    'email': 'email_queue',
    'analytics': 'analytics_queue',
    'reports': 'reports_queue',
    'cleanup': 'cleanup_queue'
}

# Webhook Events
WEBHOOK_EVENTS = {
    'user.registered': 'user.registered',
    'user.verified': 'user.verified',
    'order.created': 'order.created',
    'order.completed': 'order.completed',
    'payment.completed': 'payment.completed',
    'merchant.approved': 'merchant.approved',
    'referral.completed': 'referral.completed'
}

# Feature Flags
FEATURE_FLAGS = {
    'enable_referrals': True,
    'enable_points_system': True,
    'enable_courses': True,
    'enable_merchant_system': True,
    'enable_blog_integration': True,
    'enable_analytics': True
}