
import jwt
import os
from datetime import datetime, timedelta
from functools import wraps
from flask import request

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


def decode_token(token: str) -> dict:
    """
    Decode and validate a JWT token.
    
    Args:
        token: JWT token string
    
    Returns:
        Decoded payload dictionary
    
    Raises:
        ValueError: If token is expired or invalid
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError('Token has expired')
    except jwt.InvalidTokenError:
        raise ValueError('Invalid token')


def get_token_from_header() -> str:
    """
    Extract token from Authorization header.
    Expected format: "Bearer <token>"
    
    Returns:
        Token string
    
    Raises:
        ValueError: If token is missing or invalid format
    """
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        raise ValueError('Authorization header is missing')
    
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        raise ValueError('Invalid header format. Use: Bearer <token>')
    
    return parts[1]


def token_required(f):
    """
    Decorator to protect routes that require authentication.
    Adds 'current_user' to kwargs with user info from token.
    
    Usage:
        @app.route('/protected')
        @token_required
        def protected_route(current_user):
            return {'message': f'Hello {current_user["username"]}'}
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            token = get_token_from_header()
            payload = decode_token(token)
            
            # Add user info to kwargs
            kwargs['current_user'] = {
                'username': payload['username'],
                'role': payload['role']
            }
            
            return f(*args, **kwargs)
            
        except ValueError as e:
            return ({'Error': str(e)}, 401)
        except Exception as e:
            return ({'Error': 'Authentication failed'}, 401)
    
    return decorated
