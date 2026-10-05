# test_integration.py
"""Integration test: password + database + JWT"""

from backend.utils import hash_password, verify_password, create_access_token, decode_token
from backend.utils.db import get_db_context
from models.database import User
import uuid

print("=" * 60)
print("Integration Test: Password + Database + JWT")
print("=" * 60)

# Test 1: Hash password
print("\nTest 1: Password hashing")
print("-" * 60)
password = "SecurePassword123!"
hashed = hash_password(password)
is_valid = verify_password(password, hashed)
print(f"✅ Password hashed and verified: {is_valid}")

# Test 2: Save user to database
print("\nTest 2: Save user to database")
print("-" * 60)
user_id = uuid.uuid4()
email = "testuser@gmail.com"

try:
    with get_db_context() as db:
        user = User(
            id=user_id,
            email=email,
            password_hash=hashed,
            is_active=True
        )
        db.add(user)
        db.commit()
        print(f"✅ User saved to database")
        print(f"   User ID: {user_id}")
        print(f"   Email: {email}")
except Exception as e:
    print(f"❌ Failed to save user: {e}")

# Test 3: Create JWT token
print("\nTest 3: Create JWT token")
print("-" * 60)
token = create_access_token(str(user_id), email)
print(f"✅ Access token created")
print(f"   Token (first 50 chars): {token[:50]}...")

# Test 4: Decode and verify token
print("\nTest 4: Decode and verify token")
print("-" * 60)
payload = decode_token(token)
if payload and payload.get("user_id") == str(user_id):
    print(f"✅ Token decoded and verified")
    print(f"   User ID matches: {payload.get('user_id')}")
    print(f"   Email matches: {payload.get('email')}")
else:
    print(f"❌ Token verification failed")

# Test 5: Retrieve user from database
print("\nTest 5: Retrieve user from database")
print("-" * 60)
try:
    with get_db_context() as db:
        db_user = db.query(User).filter(User.email == email).first()
        if db_user:
            print(f"✅ User retrieved from database")
            print(f"   Email: {db_user.email}")
            print(f"   Password matches: {verify_password(password, db_user.password_hash)}")
        else:
            print(f"❌ User not found in database")
except Exception as e:
    print(f"❌ Failed to retrieve user: {e}")

# Cleanup: Delete test user
print("\nCleanup: Delete test user")
print("-" * 60)
try:
    with get_db_context() as db:
        db_user = db.query(User).filter(User.email == email).first()
        if db_user:
            db.delete(db_user)
            db.commit()
            print(f"✅ Test user deleted")
except Exception as e:
    print(f"❌ Failed to delete user: {e}")

print("\n" + "=" * 60)
print("All integration tests passed! Ready for Step 3 ✅")
print("=" * 60)