"""
User management queries - STEP BY STEP VERSION.
Starting with just password hashing.
"""
import bcrypt

# We'll add more imports later
# import data.db_connect as dbc

USER_COLLECTION = 'users'

# Field names
USERNAME = 'username'
EMAIL = 'email'
PASSWORD_HASH = 'password_hash'
ROLE = 'role'

# Roles
ROLE_USER = 'user'
ROLE_ADMIN = 'admin'


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    """
    if not password or not isinstance(password, str):
        raise ValueError('Password must be a non-empty string')
    
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify a password against its hash.
    """
    try:
        return bcrypt.checkpw(
            password.encode('utf-8'),
            password_hash.encode('utf-8')
        )
    except Exception:
        return False


