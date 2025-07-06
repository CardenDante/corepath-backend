# app/utils/helpers.py - Created by setup script
"""
CorePath Impact Utility Helper Functions
Common utility functions used across the application
"""

import re
import os
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pathlib import Path


def format_phone_number(phone: str) -> str:
    """Format phone number to consistent format"""
    if not phone:
        return phone
    
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone)
    
    # Handle Kenyan numbers
    if digits.startswith('254'):
        return f"+{digits}"
    elif digits.startswith('0') and len(digits) == 10:
        return f"+254{digits[1:]}"
    elif len(digits) == 9:
        return f"+254{digits}"
    
    return phone


def validate_kenyan_phone(phone: str) -> bool:
    """Validate Kenyan phone number format"""
    if not phone:
        return True  # Optional field
    
    # Remove spaces and special characters
    clean_phone = re.sub(r'\D', '', phone)
    
    # Check various Kenyan phone formats
    patterns = [
        r'^254[71][0-9]{8}$',  # +254 format
        r'^0[71][0-9]{8}$',    # 0 prefix format
        r'^[71][0-9]{8}$'      # Without prefix
    ]
    
    return any(re.match(pattern, clean_phone) for pattern in patterns)


def generate_filename(original_filename: str, user_id: int = None) -> str:
    """Generate unique filename for uploads"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    name, ext = os.path.splitext(original_filename)
    
    # Clean filename
    clean_name = re.sub(r'[^\w\-_\.]', '_', name)[:50]
    
    if user_id:
        return f"{user_id}_{timestamp}_{clean_name}{ext}"
    else:
        return f"{timestamp}_{clean_name}{ext}"


def get_file_hash(file_path: str) -> str:
    """Get MD5 hash of file for duplicate detection"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def ensure_directory(directory: str) -> Path:
    """Ensure directory exists, create if not"""
    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)
    return path


def format_currency(amount: float, currency: str = "KES") -> str:
    """Format currency amount"""
    if currency == "KES":
        return f"KES {amount:,.2f}"
    elif currency == "USD":
        return f"${amount:,.2f}"
    else:
        return f"{currency} {amount:,.2f}"


def calculate_points_from_amount(amount: float, rate: float = 0.01) -> int:
    """Calculate points earned from purchase amount"""
    return int(amount * rate)


def time_ago(datetime_obj: datetime) -> str:
    """Get human-readable time difference"""
    now = datetime.utcnow()
    diff = now - datetime_obj
    
    if diff.days > 0:
        return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    else:
        return "Just now"


def paginate_query(query, page: int = 1, per_page: int = 20, max_per_page: int = 100):
    """Paginate SQLAlchemy query"""
    if per_page > max_per_page:
        per_page = max_per_page
    
    offset = (page - 1) * per_page
    items = query.offset(offset).limit(per_page).all()
    total = query.count()
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
        "has_prev": page > 1,
        "has_next": page * per_page < total
    }


def clean_html(text: str) -> str:
    """Remove HTML tags from text"""
    if not text:
        return text
    
    # Simple HTML tag removal
    clean = re.sub(r'<[^>]+>', '', text)
    return clean.strip()


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug"""
    if not text:
        return ""
    
    # Convert to lowercase and replace spaces with dashes
    slug = re.sub(r'[^\w\s-]', '', text.lower())
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug.strip('-')


def mask_email(email: str) -> str:
    """Mask email for privacy (e.g., j***@example.com)"""
    if not email or '@' not in email:
        return email
    
    local, domain = email.split('@', 1)
    if len(local) <= 2:
        masked_local = local[0] + '*'
    else:
        masked_local = local[0] + '*' * (len(local) - 2) + local[-1]
    
    return f"{masked_local}@{domain}"


def mask_phone(phone: str) -> str:
    """Mask phone number for privacy"""
    if not phone:
        return phone
    
    if len(phone) <= 4:
        return '*' * len(phone)
    
    return phone[:2] + '*' * (len(phone) - 4) + phone[-2:]


def validate_file_type(filename: str, allowed_types: list) -> bool:
    """Validate file type by extension"""
    if not filename:
        return False
    
    ext = filename.lower().split('.')[-1]
    return ext in [t.lower() for t in allowed_types]


def get_file_size_mb(file_path: str) -> float:
    """Get file size in MB"""
    try:
        size_bytes = os.path.getsize(file_path)
        return size_bytes / (1024 * 1024)
    except:
        return 0.0


def create_response(data: Any = None, message: str = "", success: bool = True, **kwargs) -> Dict:
    """Create standardized API response"""
    response = {
        "success": success,
        "message": message,
        **kwargs
    }
    
    if data is not None:
        response["data"] = data
    
    return response


def extract_domain_from_email(email: str) -> str:
    """Extract domain from email address"""
    if not email or '@' not in email:
        return ""
    
    return email.split('@')[1].lower()


def is_business_email(email: str) -> bool:
    """Check if email appears to be a business email"""
    personal_domains = [
        'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
        'icloud.com', 'me.com', 'live.com', 'msn.com'
    ]
    
    domain = extract_domain_from_email(email)
    return domain and domain not in personal_domains


def calculate_age(birth_date: datetime) -> int:
    """Calculate age from birth date"""
    today = datetime.now().date()
    birth = birth_date.date() if isinstance(birth_date, datetime) else birth_date
    
    age = today.year - birth.year
    if today.month < birth.month or (today.month == birth.month and today.day < birth.day):
        age -= 1
    
    return age


def generate_order_number() -> str:
    """Generate unique order number"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    import random
    random_suffix = random.randint(1000, 9999)
    return f"CP{timestamp}{random_suffix}"


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safe division with default value for zero division"""
    try:
        return numerator / denominator if denominator != 0 else default
    except (TypeError, ZeroDivisionError):
        return default


def truncate_text(text: str, length: int = 100, suffix: str = "...") -> str:
    """Truncate text to specified length"""
    if not text or len(text) <= length:
        return text
    
    return text[:length - len(suffix)] + suffix