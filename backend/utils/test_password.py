# test_password.py
from password import hash_password, verify_password

# Test hashing
password = "MySecurePassword123!"
hashed = hash_password(password)

print(f"Original password: {password}")
print(f"Hashed password: {hashed}")
print(f"Hash length: {len(hashed)}")  # Should be 60
print()

# Test verification
is_correct = verify_password(password, hashed)
is_wrong = verify_password("WrongPassword", hashed)

print(f"Correct password? {is_correct}")  # Should be True
print(f"Wrong password? {is_wrong}")      # Should be False