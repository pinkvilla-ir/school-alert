# test_db_connection.py
from backend.utils.db import get_db_context
from models.database import User
import uuid

print("Testing database connection...")

try:
    # Test connection
    with get_db_context() as db:
        # Count existing users (should be 0)
        count = db.query(User).count()
        print(f"✅ Database connection works")
        print(f"   Existing users in DB: {count}")
        
        # Try to create a test user
        test_user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            password_hash="$2b$12$...",  # dummy hash
            is_active=True
        )
        db.add(test_user)
        db.commit()
        print(f"✅ Can create users in database")
        
        # Delete test user
        db.delete(test_user)
        db.commit()
        print(f"✅ Can delete users from database")
        
except Exception as e:
    print(f"❌ Database error: {e}")