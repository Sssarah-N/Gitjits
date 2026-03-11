"""
JWT token utilities - STEP BY STEP.
Starting with just token generation.
"""
import jwt
import os
from datetime import datetime, timedelta

# Secret key for JWT (should be in environment variable in production)
SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'dev-secret-change-in-production')
ALGORITHM = 'HS256'
TOKEN_EXPIRY_HOURS = 24


def generate_token(username: str, role: str) -> str:
    """
    Generate a JWT token for a user.
    
    Args:
        username: User's username
        role: User's role (admin, user, etc.)
    
    Returns:
        JWT token string
    """
    payload = {
        'username': username,
        'role': role,
        'exp': datetime.utcnow() + timedelta(hours=TOKEN_EXPIRY_HOURS),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# add more functions later:
# - decode_token()
# - token_required decorator
