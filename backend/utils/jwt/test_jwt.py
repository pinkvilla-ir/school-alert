# test_jwt.py
import time
from manager import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_user_id_from_token,
)

print("=" * 60)
print("Testing JWT Token Creation and Validation")
print("=" * 60)

# Test data
user_id = "550e8400-e29b-41d4-a716-446655440000"
email = "mom@gmail.com"

print(f"\nUser ID: {user_id}")
print(f"Email: {email}\n")

# ═══════════════════════════════════════════════════════════
# Test 1: Create and validate access token
# ═══════════════════════════════════════════════════════════
print("Test 1: Access Token (15 minutes)")
print("-" * 60)

access_token = create_access_token(user_id, email)
print(f"Created token: {access_token[:50]}...")
print(f"Token length: {len(access_token)}")

# Decode it
payload = decode_token(access_token, token_type="access")
if payload:
    print(f"✅ Token is valid")
    print(f"   User ID: {payload.get('user_id')}")
    print(f"   Email: {payload.get('email')}")
    print(f"   Type: {payload.get('type')}")
    print(f"   Expires in ~15 minutes")
else:
    print(f"❌ Token is invalid")

# ═══════════════════════════════════════════════════════════
# Test 2: Create and validate refresh token
# ═══════════════════════════════════════════════════════════
print("\n\nTest 2: Refresh Token (7 days)")
print("-" * 60)

refresh_token = create_refresh_token(user_id)
print(f"Created token: {refresh_token[:50]}...")
print(f"Token length: {len(refresh_token)}")

# Decode it
payload = decode_token(refresh_token, token_type="refresh")
if payload:
    print(f"✅ Token is valid")
    print(f"   User ID: {payload.get('user_id')}")
    print(f"   Type: {payload.get('type')}")
    print(f"   Expires in ~7 days")
else:
    print(f"❌ Token is invalid")

# ═══════════════════════════════════════════════════════════
# Test 3: Extract user_id from token
# ═══════════════════════════════════════════════════════════
print("\n\nTest 3: Extract user_id from token")
print("-" * 60)

extracted_user_id = get_user_id_from_token(access_token)
if extracted_user_id == user_id:
    print(f"✅ Extracted user_id matches")
    print(f"   Original: {user_id}")
    print(f"   Extracted: {extracted_user_id}")
else:
    print(f"❌ User IDs don't match")

# ═══════════════════════════════════════════════════════════
# Test 4: Invalid token type
# ═══════════════════════════════════════════════════════════
print("\n\nTest 4: Invalid token type (security check)")
print("-" * 60)

# Try to use access token as refresh token (should fail)
payload = decode_token(access_token, token_type="refresh")
if payload is None:
    print(f"✅ Correctly rejected access token when expecting refresh token")
else:
    print(f"❌ Security issue: accepted wrong token type")

# ═══════════════════════════════════════════════════════════
# Test 5: Expired token (simulated)
# ═══════════════════════════════════════════════════════════
print("\n\nTest 5: Corrupted/invalid token")
print("-" * 60)

invalid_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature"
payload = decode_token(invalid_token)
if payload is None:
    print(f"✅ Correctly rejected invalid token")
else:
    print(f"❌ Security issue: accepted invalid token")

print("\n" + "=" * 60)
print("All tests completed!")
print("=" * 60)