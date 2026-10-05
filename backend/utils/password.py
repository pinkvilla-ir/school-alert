# utils/password.py
"""Password hashing and verification utilities."""

import bcrypt
from typing import Tuple


class PasswordManager:
    """Handle password hashing and verification."""

    # Bcrypt cost factor (higher = slower but more secure)
    # 12 is recommended: strong security + reasonable speed
    SALT_ROUNDS = 12

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a plaintext password using bcrypt.
        
        Args:
            password: The plaintext password to hash
            
        Returns:
            The hashed password (includes salt)
            
        Example:
            hashed = PasswordManager.hash_password("secure123")
            # Returns: $2b$12$... (60 chars)
        """
        # Convert password to bytes
        password_bytes = password.encode('utf-8')
        
        # Generate salt and hash in one call
        salt = bcrypt.gensalt(rounds=PasswordManager.SALT_ROUNDS)
        hashed = bcrypt.hashpw(password_bytes, salt)
        
        # Return as string
        return hashed.decode('utf-8')

    @staticmethod
    def verify_password(plaintext_password: str, hashed_password: str) -> bool:
        """
        Verify a plaintext password against its hash.
        
        Args:
            plaintext_password: The password user entered
            hashed_password: The hash stored in database
            
        Returns:
            True if password matches, False otherwise
            
        Example:
            is_valid = PasswordManager.verify_password("secure123", hashed)
            # Returns: True or False
        """
        try:
            # Convert to bytes
            plaintext_bytes = plaintext_password.encode('utf-8')
            hashed_bytes = hashed_password.encode('utf-8')
            
            # Compare
            return bcrypt.checkpw(plaintext_bytes, hashed_bytes)
        except (ValueError, TypeError):
            # Invalid hash format
            return False


# Convenience functions for direct use
def hash_password(password: str) -> str:
    """Quick hash function."""
    return PasswordManager.hash_password(password)


def verify_password(plaintext: str, hashed: str) -> bool:
    """Quick verify function."""
    return PasswordManager.verify_password(plaintext, hashed)