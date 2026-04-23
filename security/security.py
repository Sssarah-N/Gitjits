"""
Security module for authentication and authorization.

Security record format:
{
    feature_name: {
        create/read/update/delete: {
            user_list: [],  # Specific users (empty = any authenticated)
            checks: {
                login: True,  # Requires authentication
                admin_only: False,  # Requires admin role
                # Additional checks can be added here
            },
        },
    },
}
"""
import jwt
import os
from datetime import datetime, timedelta
from functools import wraps
from flask import request

# import data.db_connect as dbc

# =============================================================================
# JWT Configuration
# =============================================================================
SECRET_KEY = os.environ.get(
    'JWT_SECRET_KEY', 'dev-secret-change-in-production'
)
ALGORITHM = 'HS256'
TOKEN_EXPIRY_HOURS = 24

# =============================================================================
# Security Protocol Constants
# =============================================================================
COLLECT_NAME = 'security'
CREATE = 'create'
READ = 'read'
UPDATE = 'update'
DELETE = 'delete'
USER_LIST = 'user_list'
CHECKS = 'checks'
LOGIN = 'login'
ADMIN_ONLY = 'admin_only'

# Feature Names
PEOPLE = 'people'
PARKS = 'parks'
DEV_LOGS = 'dev_logs'
AUTH = 'auth'

# =============================================================================
# Security Protocol Records
# =============================================================================
security_recs = None
# These define the security requirements for each feature and operation
temp_recs = {
    PARKS: {
        CREATE: {
            USER_LIST: [],  # Only admins
            CHECKS: {
                LOGIN: True,
                ADMIN_ONLY: True,
            },
        },
        DELETE: {
            USER_LIST: [],  # Only admins
            CHECKS: {
                LOGIN: True,
                ADMIN_ONLY: True,
            },
        },
    },
    DEV_LOGS: {
        READ: {
            USER_LIST: [],  # Only admins
            CHECKS: {
                LOGIN: True,
                ADMIN_ONLY: True,  # Requires admin role
            },
        },
    },
    AUTH: {
        CREATE: {  # User registration
            USER_LIST: [],  # Public - anyone can register
            CHECKS: {
                LOGIN: False,
            },
        },
    },
}


def read() -> dict:
    global security_recs
    # dbc.read()
    security_recs = temp_recs
    return security_recs


def needs_recs(fn):
    """
    Should be used to decorate any function that directly accesses sec recs.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        global security_recs
        if not security_recs:
            security_recs = read()
        return fn(*args, **kwargs)
    return wrapper


@needs_recs
def read_feature(feature_name: str) -> dict:
    if feature_name in security_recs:
        return security_recs[feature_name]
    else:
        return None


# =============================================================================
# JWT Authentication Functions
# =============================================================================

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


# =============================================================================
# Security Decorators
# =============================================================================

def token_required(f):
    """
    Decorator to protect routes that require authentication.
    Adds 'current_user' to kwargs with user info from token.

    Security Protocol: Implements LOGIN check from security records.

    Usage:
        @app.route('/protected')
        @token_required
        def protected_route(current_user):
            return {'message': f'Hello {current_user["username"]}'}
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # Authentication phase - catch only auth-related errors
        try:
            token = get_token_from_header()
            payload = decode_token(token)
        except ValueError as err:
            return ({'Error': str(err)}, 401)
        except Exception:
            return ({'Error': 'Authentication failed'}, 401)

        # Add user info to kwargs
        kwargs['current_user'] = {
            'username': payload['username'],
            'role': payload['role']
        }

        # Call the wrapped function - let its exceptions propagate
        return f(*args, **kwargs)

    return decorated


def admin_required(f):
    """
    Decorator for admin-only routes.
    Checks authentication AND admin role.

    Security Protocol: Implements LOGIN + ADMIN_ONLY checks
    from security records.

    Usage:
        @app.route('/admin/logs')
        @admin_required
        def admin_route(current_user):
            return {'logs': [...]}
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # Authentication phase - catch only auth-related errors
        try:
            token = get_token_from_header()
            payload = decode_token(token)
        except ValueError as err:
            return ({'Error': str(err)}, 401)
        except Exception:
            return ({'Error': 'Authentication failed'}, 401)

        # Check if user is admin
        if payload.get('role') != 'admin':
            return ({'Error': 'Admin access required'}, 403)

        # Add user info to kwargs
        kwargs['current_user'] = {
            'username': payload['username'],
            'role': payload['role']
        }

        # Call the wrapped function - let its exceptions propagate
        return f(*args, **kwargs)

    return decorated
