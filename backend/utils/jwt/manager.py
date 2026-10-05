# utils/jwt/manager.py
"""JWT token creation and validation utilities."""

import jwt
from datetime import datetime, timedelta
from typing import Dict, Optional
import os
from uuid import UUID


class JWTManager:
    """Handle JWT token creation and validation."""

    # Get secret key from environment, fallback to default (dev only)
    SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    
    # Algorithms supported
    ALGORITHM = "HS256"
    
    # Token expiration times
    ACCESS_TOKEN_EXPIRE_MINUTES = 15      # Short-lived
    REFRESH_TOKEN_EXPIRE_DAYS = 7         # Long-lived

    @staticmethod
    def create_access_token(user_id: str, email: str) -> str:
        """
        Create a short-lived access token (15 minutes).
        
        Args:
            user_id: UUID of the user
            email: Email address of the user
            
        Returns:
            JWT access token string
            
        Example:
            token = JWTManager.create_access_token("uuid-123", "mom@gmail.com")
        """
        now = datetime.utcnow()
        expires = now + timedelta(minutes=JWTManager.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        payload = {
            "user_id": str(user_id),
            "email": email,
            "type": "access",
            "iat": now,          # Issued at
            "exp": expires,      # Expiration time
        }
        
        token = jwt.encode(
            payload,
            JWTManager.SECRET_KEY,
            algorithm=JWTManager.ALGORITHM
        )
        
        return token

    @staticmethod
    def create_refresh_token(user_id: str) -> str:
        """
        Create a long-lived refresh token (7 days).
        
        Args:
            user_id: UUID of the user
            
        Returns:
            JWT refresh token string
            
        Example:
            token = JWTManager.create_refresh_token("uuid-123")
        """
        now = datetime.utcnow()
        expires = now + timedelta(days=JWTManager.REFRESH_TOKEN_EXPIRE_DAYS)
        
        payload = {
            "user_id": str(user_id),
            "type": "refresh",
            "iat": now,
            "exp": expires,
        }
        
        token = jwt.encode(
            payload,
            JWTManager.SECRET_KEY,
            algorithm=JWTManager.ALGORITHM
        )
        
        return token

    @staticmethod
    def decode_token(token: str, token_type: str = "access") -> Optional[Dict]:
        """
        Decode and validate a JWT token.
        
        Args:
            token: JWT token string
            token_type: "access" or "refresh" (validates token type)
            
        Returns:
            Payload dict if valid, None if invalid or expired
            
        Example:
            payload = JWTManager.decode_token(token)
            if payload:
                user_id = payload.get("user_id")
        """
        try:
            payload = jwt.decode(
                token,
                JWTManager.SECRET_KEY,
                algorithms=[JWTManager.ALGORITHM]
            )
            
            # Validate token type
            if payload.get("type") != token_type:
                return None
            
            return payload
            
        except jwt.ExpiredSignatureError:
            # Token has expired
            return None
        except jwt.InvalidTokenError:
            # Invalid token (corrupted, wrong secret, etc)
            return None
        except Exception as e:
            # Unexpected error
            return None

    @staticmethod
    def decode_access_token(token: str) -> Optional[Dict]:
        """Convenience method to decode access token."""
        return JWTManager.decode_token(token, token_type="access")

    @staticmethod
    def decode_refresh_token(token: str) -> Optional[Dict]:
        """Convenience method to decode refresh token."""
        return JWTManager.decode_token(token, token_type="refresh")


# Convenience functions for direct use
def create_access_token(user_id: str, email: str) -> str:
    """Create access token."""
    return JWTManager.create_access_token(user_id, email)


def create_refresh_token(user_id: str) -> str:
    """Create refresh token."""
    return JWTManager.create_refresh_token(user_id)


def decode_token(token: str, token_type: str = "access") -> Optional[Dict]:
    """Decode token."""
    return JWTManager.decode_token(token, token_type)


def get_user_id_from_token(token: str) -> Optional[str]:
    """Extract user_id from token. Returns None if invalid."""
    payload = decode_token(token)
    if payload:
        return payload.get("user_id")
    return None