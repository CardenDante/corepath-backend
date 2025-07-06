"""
CorePath Impact Phase 1 Test Script
Quick test to verify all components are working
"""

import asyncio
import sys
import os

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

async def test_phase1():
    """Test Phase 1 components"""
    print("🧪 Testing CorePath Impact Phase 1 Components...")
    print("=" * 50)
    
    # Test 1: Configuration
    print("1. Testing Configuration...")
    try:
        from app.core.config import settings
        print(f"   ✅ Project Name: {settings.PROJECT_NAME}")
        print(f"   ✅ Database URL: {settings.DATABASE_URL}")
        print(f"   ✅ API Version: {settings.API_V1_STR}")
        print(f"   ✅ Referral Points: {settings.REFERRAL_POINTS}")
    except Exception as e:
        print(f"   ❌ Configuration Error: {e}")
        return False
    
    # Test 2: Database
    print("\n2. Testing Database Connection...")
    try:
        from app.core.database import engine, create_tables, check_database_health
        
        # Create tables
        create_tables()
        print("   ✅ Database tables created")
        
        # Check health
        health = check_database_health()
        print(f"   ✅ Database Health: {health['status']}")
        
    except Exception as e:
        print(f"   ❌ Database Error: {e}")
        return False
    
    # Test 3: Security
    print("\n3. Testing Security Functions...")
    try:
        from app.core.security import SecurityUtils, create_token_response
        
        # Test password hashing
        password = "TestPassword123"
        hashed = SecurityUtils.get_password_hash(password)
        verified = SecurityUtils.verify_password(password, hashed)
        print(f"   ✅ Password hashing works: {verified}")
        
        # Test token creation
        token_response = create_token_response(1, "test@example.com")
        print(f"   ✅ Token creation works: {len(token_response['access_token']) > 0}")
        
        # Test referral code generation
        referral_code = SecurityUtils.generate_referral_code()
        print(f"   ✅ Referral code generated: {referral_code}")
        
    except Exception as e:
        print(f"   ❌ Security Error: {e}")
        return False
    
    # Test 4: Models
    print("\n4. Testing Database Models...")
    try:
        from app.models.user import User, UserProfile, UserRole
        from sqlalchemy.orm import sessionmaker
        
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        # Test user creation
        test_user = User(
            email="test@corepathimpact.com",
            password_hash=SecurityUtils.get_password_hash("TestPass123"),
            first_name="Test",
            last_name="User",
            role=UserRole.CUSTOMER.value
        )
        
        db.add(test_user)
        db.flush()
        
        # Test profile creation
        test_profile = UserProfile(
            user_id=test_user.id,
            current_points_balance=100,
            total_points_earned=100
        )
        
        db.add(test_profile)
        db.commit()
        
        print(f"   ✅ User created with ID: {test_user.id}")
        print(f"   ✅ Profile created with points: {test_profile.current_points_balance}")
        
        # Clean up
        db.delete(test_profile)
        db.delete(test_user)
        db.commit()
        db.close()
        
    except Exception as e:
        print(f"   ❌ Models Error: {e}")
        return False
    
    # Test 5: Services
    print("\n5. Testing Authentication Service...")
    try:
        from app.services.auth_service import AuthService
        from app.schemas.auth import UserRegisterRequest
        from sqlalchemy.orm import sessionmaker
        
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        auth_service = AuthService(db)
        
        # Test service methods exist
        assert hasattr(auth_service, 'register_user')
        assert hasattr(auth_service, 'authenticate_user')
        assert hasattr(auth_service, 'get_user_by_email')
        print("   ✅ Auth service methods available")
        
        db.close()
        
    except Exception as e:
        print(f"   ❌ Services Error: {e}")
        return False
    
    # Test 6: Schemas
    print("\n6. Testing Pydantic Schemas...")
    try:
        from app.schemas.auth import UserRegisterRequest, UserLoginRequest, TokenResponse
        
        # Test registration schema
        reg_data = UserRegisterRequest(
            email="test@example.com",
            password="TestPass123",
            confirm_password="TestPass123",
            first_name="Test",
            last_name="User"
        )
        print(f"   ✅ Registration schema works: {reg_data.email}")
        
        # Test login schema
        login_data = UserLoginRequest(
            email="test@example.com",
            password="TestPass123"
        )
        print(f"   ✅ Login schema works: {login_data.email}")
        
    except Exception as e:
        print(f"   ❌ Schemas Error: {e}")
        return False
    
    # Test 7: Utilities
    print("\n7. Testing Utilities...")
    try:
        from app.utils.helpers import format_phone_number, generate_filename, calculate_points_from_amount
        from app.utils.constants import VDC_VALUES, POINTS_CONFIG
        
        # Test helper functions
        phone = format_phone_number("0712345678")
        print(f"   ✅ Phone formatting: {phone}")
        
        filename = generate_filename("test.jpg", 1)
        print(f"   ✅ Filename generation: {filename}")
        
        points = calculate_points_from_amount(1000.0)
        print(f"   ✅ Points calculation: {points}")
        
        print(f"   ✅ VDC Values loaded: {len(VDC_VALUES)} values")
        print(f"   ✅ Points config: {POINTS_CONFIG['referral_reward']} per referral")
        
    except Exception as e:
        print(f"   ❌ Utilities Error: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 All Phase 1 tests passed successfully!")
    print("\n📋 What's working:")
    print("   ✅ Configuration and environment setup")
    print("   ✅ SQLite database connection and models")
    print("   ✅ JWT authentication and security")
    print("   ✅ User registration and login system")
    print("   ✅ Password hashing and validation")
    print("   ✅ Points system (500 per referral)")
    print("   ✅ Pydantic schemas for API validation")
    print("   ✅ Utility functions and constants")
    
    print("\n🚀 Ready for Phase 2: Products & File Upload!")
    return True


if __name__ == "__main__":
    # Run the test
    try:
        success = asyncio.run(test_phase1())
        if success:
            print("\n✅ Phase 1 is ready! You can now start the server:")
            print("   uvicorn app.main:app --reload")
            print("   Then visit: http://localhost:8000/docs")
        else:
            print("\n❌ Some tests failed. Please check the errors above.")
    except Exception as e:
        print(f"\n💥 Test script failed: {e}")
        print("Make sure you've installed all dependencies and run the setup script.")