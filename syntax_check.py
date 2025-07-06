# debug_import.py
import sys
import os

print("=== Debug Admin Import ===")
print(f"Python version: {sys.version}")
print(f"Current working directory: {os.getcwd()}")

# Check if file exists
admin_file = "app/api/v1/endpoints/admin.py"
print(f"Admin file exists: {os.path.exists(admin_file)}")

if os.path.exists(admin_file):
    with open(admin_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"File size: {len(content)} characters")
    print(f"Contains 'router = APIRouter()': {'router = APIRouter()' in content}")
    print(f"Contains 'from fastapi import APIRouter': {'from fastapi import APIRouter' in content}")
    
    # Show first 500 characters
    print("\nFirst 500 characters:")
    print(content[:500])

# Try importing step by step
print("\n=== Step by step import ===")

try:
    print("1. Importing app...")
    import app
    print("   ✅ Success")
except Exception as e:
    print(f"   ❌ Failed: {e}")

try:
    print("2. Importing app.api...")
    import app.api
    print("   ✅ Success")
except Exception as e:
    print(f"   ❌ Failed: {e}")

try:
    print("3. Importing app.api.v1...")
    import app.api.v1
    print("   ✅ Success")
except Exception as e:
    print(f"   ❌ Failed: {e}")

try:
    print("4. Importing app.api.v1.endpoints...")
    import app.api.v1.endpoints
    print("   ✅ Success")
except Exception as e:
    print(f"   ❌ Failed: {e}")

try:
    print("5. Importing app.api.v1.endpoints.admin...")
    import app.api.v1.endpoints.admin as admin_module
    print("   ✅ Success")
    print(f"   Module: {admin_module}")
    print(f"   Module file: {getattr(admin_module, '__file__', 'No file')}")
    print(f"   Has router: {hasattr(admin_module, 'router')}")
    if hasattr(admin_module, 'router'):
        print(f"   Router type: {type(admin_module.router)}")
    else:
        print("   Available attributes:", [attr for attr in dir(admin_module) if not attr.startswith('_')])
except Exception as e:
    print(f"   ❌ Failed: {e}")
    import traceback
    traceback.print_exc()