# test_import.py
try:
    from app.api.v1.endpoints import admin
    print("✅ Admin import successful")
    print(f"✅ Router found: {hasattr(admin, 'router')}")
    if hasattr(admin, 'router'):
        print(f"✅ Router type: {type(admin.router)}")
    else:
        print("❌ No router attribute found")
except Exception as e:
    print(f"❌ Import failed: {e}")